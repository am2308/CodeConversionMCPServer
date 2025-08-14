"""
AWS Lambda handler for CodeConversion FastAPI application
"""
import os
import json
import boto3
from mangum import Mangum

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager')
s3_client = boto3.client('s3')

# Global variable to store the app instance
app = None

def load_secrets_from_aws():
    """Load secrets from AWS Secrets Manager and S3"""
    try:
        # Load GitHub App secrets
        github_secret_name = os.environ.get('GITHUB_APP_SECRET_NAME')
        if github_secret_name:
            github_response = secrets_client.get_secret_value(SecretId=github_secret_name)
            github_secrets = json.loads(github_response['SecretString'])
            
            # Map GitHub secrets to expected environment variable names
            for key, value in github_secrets.items():
                os.environ[key.lower()] = value  # Convert to lowercase for pydantic
        
        # Load application secrets
        app_secret_name = os.environ.get('APP_SECRET_NAME')
        if app_secret_name:
            app_response = secrets_client.get_secret_value(SecretId=app_secret_name)
            app_secrets = json.loads(app_response['SecretString'])
            
            # Map application secrets to expected environment variable names
            for key, value in app_secrets.items():
                os.environ[key.lower()] = value  # Convert to lowercase for pydantic
        
        # Load database credentials
        db_secret_arn = os.environ.get('DATABASE_SECRET_ARN')
        if db_secret_arn:
            db_response = secrets_client.get_secret_value(SecretId=db_secret_arn)
            db_secrets = json.loads(db_response['SecretString'])
            
            # Construct database URL and set required environment variables
            db_host = os.environ.get('DATABASE_HOST')
            db_port = os.environ.get('DATABASE_PORT', '5432')
            db_name = os.environ.get('DATABASE_NAME', 'codeconversion')
            username = db_secrets.get('username')
            password = db_secrets.get('password')
            
            if username and password:
                database_url = f"postgresql://{username}:{password}@{db_host}:{db_port}/{db_name}"
                # Set both expected variable names
                os.environ['database_url'] = database_url
                os.environ['DATABASE_URL'] = database_url  # Legacy support
                os.environ['postgres_password'] = password  # Required by config
        
        # Download GitHub App private key from S3
        secrets_bucket = os.environ.get('SECRETS_BUCKET')
        private_key_path = os.environ.get('GITHUB_APP_PRIVATE_KEY_PATH')
        
        if secrets_bucket and private_key_path:
            try:
                # Download private key to /tmp (Lambda's writable directory)
                local_key_path = f"/tmp/{os.path.basename(private_key_path)}"
                s3_client.download_file(secrets_bucket, private_key_path, local_key_path)
                os.environ['github_app_private_key_path'] = local_key_path
                os.environ['GITHUB_APP_PRIVATE_KEY_PATH'] = local_key_path  # Legacy support
            except Exception as e:
                print(f"Warning: Could not download private key from S3: {e}")
        
        print("Successfully loaded secrets from AWS")
        
    except Exception as e:
        print(f"Error loading secrets from AWS: {e}")
# Load secrets when the module is imported (Lambda container reuse)
load_secrets_from_aws()

# Import the app AFTER secrets are loaded
from src.main import app

# Create Mangum handler
mangum_handler = Mangum(app, lifespan="off")

def handler(event, context):
    """
    AWS Lambda handler function (main entry point)
    """
    try:
        # Set additional environment variables for Lambda
        os.environ['AWS_LAMBDA_FUNCTION_NAME'] = context.function_name
        os.environ['AWS_REQUEST_ID'] = context.aws_request_id
        
        # Call the Mangum handler
        return mangum_handler(event, context)
        
    except Exception as e:
        print(f"Lambda handler error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        }

# Legacy alias for compatibility
lambda_handler = handler

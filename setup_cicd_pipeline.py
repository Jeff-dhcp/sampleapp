import boto3

# Initialize clients
codepipeline = boto3.client('codepipeline')
codebuild = boto3.client('codebuild')
elasticbeanstalk = boto3.client('elasticbeanstalk')

# Configuration
REPO_NAME = "sample-app"
GITHUB_OWNER = "<your-github-username>"
GITHUB_REPO = "<your-github-repo>"
GITHUB_BRANCH = "main"
GITHUB_TOKEN = "<your-github-token>"
BUCKET_NAME = "<your-s3-bucket-for-artifacts>"
APPLICATION_NAME = "SampleApp"
ENVIRONMENT_NAME = "SampleAppEnv"

# Step 1: Create Elastic Beanstalk Application and Environment
def create_beanstalk_app():
    print("Creating Elastic Beanstalk Application...")
    elasticbeanstalk.create_application(ApplicationName=APPLICATION_NAME)

    print("Creating Elastic Beanstalk Environment...")
    elasticbeanstalk.create_environment(
        ApplicationName=APPLICATION_NAME,
        EnvironmentName=ENVIRONMENT_NAME,
        SolutionStackName="64bit Amazon Linux 2 v3.5.6 running Python 3.8",
    )
    print("Elastic Beanstalk environment created.")

# Step 2: Create CodeBuild Project
def create_codebuild_project():
    print("Creating CodeBuild project...")
    codebuild.create_project(
        name=REPO_NAME,
        source={
            'type': 'GITHUB',
            'location': f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}.git",
            'buildspec': 'buildspec.yml',
            'auth': {'type': 'OAUTH', 'resource': GITHUB_TOKEN}
        },
        artifacts={'type': 'CODEPIPELINE'},
        environment={
            'type': 'LINUX_CONTAINER',
            'image': 'aws/codebuild/standard:5.0',
            'computeType': 'BUILD_GENERAL1_SMALL',
            'environmentVariables': [
                {'name': 'AWS_DEFAULT_REGION', 'value': 'us-east-1'}
            ]
        },
        serviceRole='<your-codebuild-service-role-arn>',
    )
    print("CodeBuild project created.")

# Step 3: Create CodePipeline
def create_codepipeline():
    print("Creating CodePipeline...")
    pipeline = {
        'pipeline': {
            'name': REPO_NAME,
            'roleArn': '<your-codepipeline-service-role-arn>',
            'artifactStore': {
                'type': 'S3',
                'location': BUCKET_NAME
            },
            'stages': [
                {
                    'name': 'Source',
                    'actions': [
                        {
                            'name': 'GitHubSource',
                            'actionTypeId': {
                                'category': 'Source',
                                'owner': 'ThirdParty',
                                'provider': 'GitHub',
                                'version': '1'
                            },
                            'configuration': {
                                'Owner': GITHUB_OWNER,
                                'Repo': GITHUB_REPO,
                                'Branch': GITHUB_BRANCH,
                                'OAuthToken': GITHUB_TOKEN
                            },
                            'outputArtifacts': [{'name': 'SourceOutput'}],
                        }
                    ]
                },
                {
                    'name': 'Build',
                    'actions': [
                        {
                            'name': 'CodeBuild',
                            'actionTypeId': {
                                'category': 'Build',
                                'owner': 'AWS',
                                'provider': 'CodeBuild',
                                'version': '1'
                            },
                            'configuration': {
                                'ProjectName': REPO_NAME
                            },
                            'inputArtifacts': [{'name': 'SourceOutput'}],
                            'outputArtifacts': [{'name': 'BuildOutput'}],
                        }
                    ]
                },
                {
                    'name': 'Deploy',
                    'actions': [
                        {
                            'name': 'DeployToElasticBeanstalk',
                            'actionTypeId': {
                                'category': 'Deploy',
                                'owner': 'AWS',
                                'provider': 'ElasticBeanstalk',
                                'version': '1'
                            },
                            'configuration': {
                                'ApplicationName': APPLICATION_NAME,
                                'EnvironmentName': ENVIRONMENT_NAME
                            },
                            'inputArtifacts': [{'name': 'BuildOutput'}],
                        }
                    ]
                }
            ]
        }
    }
    codepipeline.create_pipeline(**pipeline)
    print("CodePipeline created.")

# Main function
if __name__ == "__main__":
    create_beanstalk_app()
    create_codebuild_project()
    create_codepipeline()
    print("CI/CD pipeline setup complete.")

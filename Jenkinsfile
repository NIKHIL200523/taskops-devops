pipeline {
    agent any
    stages {
        stage('Checkout Git') {
            steps {
                echo 'Pulling latest source code from GitHub...'
            }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t taskops-app:latest .'
            }
        }
        stage('Automated Smoke Test') {
            steps {
                sh 'docker run --rm taskops-app:latest python -c "import app; client = app.app.test_client(); assert client.get(\'/api/health\').status_code == 200; print(\'HEALTH CHECK PASSED\')"'
            }
        }
        stage('Deploy Container on AWS') {
            steps {
                sh 'docker stop taskops-container || true'
                sh 'docker rm taskops-container || true'
                sh 'docker run -d --name taskops-container -v taskops-data:/app/data -p 5000:5000 taskops-app:latest'
            }
        }
    }
}
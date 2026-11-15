pipeline {
    agent any
    stages {
        stage('Checkout Git') {
            steps {
                echo 'Pulling latest code from Git repository...'
            }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t taskops-app:latest .'
            }
        }
        stage('Deploy Container on AWS') {
            steps {
                sh 'docker stop taskops-container || true'
                sh 'docker rm taskops-container || true'
                sh 'docker run -d --name taskops-container -p 5000:5000 taskops-app:latest'
            }
        }
    }
}
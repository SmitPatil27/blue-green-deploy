pipeline {
    agent any

    environment {
        IMAGE_NAME = "egxsmit/blue-green"
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
        KUBECONFIG = "C:\\Users\\Smit Patil\\.kube\\config"
    }

    stages {

        stage('1. Checkout') {
            steps {
                git branch: 'main',
                    credentialsId: 'github-creds',
                    url: 'https://github.com/SmitPatil27/blue-green-deploy.git'
                echo "Code checked out"
            }
        }

        stage('2. Test') {
            steps {
                bat 'pip install -r requirements.txt'
                bat 'pytest test_app.py -v'
                echo "Tests passed"
            }
        }

        stage('3. Build and Push Image') {
            steps {
                bat "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    bat "docker login -u %DOCKER_USER% -p %DOCKER_PASS%"
                    bat "docker push ${IMAGE_NAME}:${IMAGE_TAG}"
                }
                echo "Image pushed"
            }
        }

       stage('4. Detect Active Slot') {
    steps {
        script {
            bat 'kubectl config use-context docker-desktop'

            def activeSlot = bat(
                script: 'kubectl get svc python-app-service -o jsonpath="{.spec.selector.slot}"',
                returnStdout: true
            ).trim()

            if (!activeSlot) {
                activeSlot = "blue"
            }

            echo "Active Slot: ${activeSlot}"

            env.ACTIVE_SLOT = activeSlot
            env.INACTIVE_SLOT = (activeSlot == "blue") ? "green" : "blue"

            echo "Deploying to: ${env.INACTIVE_SLOT}"
        }
    }
}
        stage('5. Deploy to Inactive Slot') {
            steps {
                script {
                    def deployFile = "k8s/${env.DEPLOY_SLOT}-deployment.yaml"
                    def tagPlaceholder = "${env.DEPLOY_SLOT.toUpperCase()}_TAG"
                    bat "powershell -Command \"(Get-Content ${deployFile}) -replace '${tagPlaceholder}','${IMAGE_TAG}' | Set-Content ${deployFile}\""
                    bat "kubectl apply -f ${deployFile} --validate=false"
                    bat "kubectl rollout status deployment/python-app-${env.DEPLOY_SLOT} --timeout=120s"
                    echo "Deployed to ${env.DEPLOY_SLOT}"
                }
            }
        }

        stage('6. Switch Traffic') {
            steps {
                script {
                    writeFile file: 'patch.json', text: "{\"spec\":{\"selector\":{\"app\":\"python-app\",\"slot\":\"${env.DEPLOY_SLOT}\"}}}"
                    bat "kubectl patch svc python-app-service --type=merge --patch-file=patch.json"
                    echo "Traffic switched to ${env.DEPLOY_SLOT}"
                }
            }
        }

        stage('7. Verify') {
            steps {
                bat 'kubectl get pods --show-labels'
                bat 'kubectl get svc python-app-service'
                echo "Blue-Green deploy complete! ${env.DEPLOY_SLOT} is now LIVE"
            }
        }
    }

    post {
        success {
            echo "SUCCESS - ${env.DEPLOY_SLOT} slot is live with build ${IMAGE_TAG}"
        }
        failure {
            echo "FAILED - ${env.ACTIVE_SLOT} slot still live, no impact"
        }
        always {
            bat "docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || exit 0"
        }
    }
}

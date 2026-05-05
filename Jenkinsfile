pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'egxsmit/blue-green'
        DOCKER_TAG   = "${env.BUILD_NUMBER}"
    }

    stages {

        // 1️⃣ Checkout
        stage('1. Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/SmitPatil27/blue-green-deploy.git',
                    credentialsId: 'github-creds'
                echo 'Code checked out'
            }
        }

        // 2️⃣ Test
        stage('2. Test') {
            steps {
                bat 'pip install -r requirements.txt'
                bat 'pytest test_app.py -v'
                echo 'Tests passed'
            }
        }

        // 3️⃣ Build & Push Docker Image
        stage('3. Build and Push Image') {
            steps {
                bat "docker build -t %DOCKER_IMAGE%:%DOCKER_TAG% ."

                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    bat "echo %DOCKER_PASS% | docker login -u %DOCKER_USER% --password-stdin"
                    bat "docker push %DOCKER_IMAGE%:%DOCKER_TAG%"
                }

                echo 'Image pushed'
            }
        }

        // 4️⃣ Ensure Service Exists (IMPORTANT FIX)
        stage('4. Init Kubernetes') {
            steps {
                bat 'kubectl config use-context docker-desktop'
                bat 'kubectl apply -f k8s/service.yaml'
            }
        }

        // 5️⃣ Detect Active Slot (FIXED)
        stage('5. Detect Active Slot') {
            steps {
                script {
                    def activeSlot = bat(
                        script: 'kubectl get svc python-app-service -o jsonpath="{.spec.selector.slot}" 2>nul',
                        returnStdout: true
                    ).trim()

                    if (!activeSlot) {
                        echo "No active slot found → defaulting to BLUE"
                        activeSlot = "blue"
                    }

                    env.ACTIVE_SLOT = activeSlot
                    env.INACTIVE_SLOT = (activeSlot == "blue") ? "green" : "blue"

                    echo "Active Slot: ${env.ACTIVE_SLOT}"
                    echo "Deploying to: ${env.INACTIVE_SLOT}"
                }
            }
        }

        // 6️⃣ Deploy to Inactive Slot
        stage('6. Deploy to Inactive Slot') {
            steps {
                script {
                    if (env.INACTIVE_SLOT == "blue") {
                        bat "kubectl apply -f k8s/blue-deployment.yaml"
                        bat "kubectl set image deployment/python-app-blue python-app=%DOCKER_IMAGE%:%DOCKER_TAG%"
                        bat "kubectl rollout status deployment/python-app-blue"
                    } else {
                        bat "kubectl apply -f k8s/green-deployment.yaml"
                        bat "kubectl set image deployment/python-app-green python-app=%DOCKER_IMAGE%:%DOCKER_TAG%"
                        bat "kubectl rollout status deployment/python-app-green"
                    }
                }
            }
        }

        // 7️⃣ Switch Traffic
        stage('7. Switch Traffic') {
            steps {
                script {
                    bat """
                        kubectl patch svc python-app-service --type=merge -p "{""spec"":{""selector"":{""app"":""python-app"",""slot"":""${env.INACTIVE_SLOT}""}}}"
                    """
                    echo "Traffic switched to ${env.INACTIVE_SLOT}"
                }
            }
        }

        // 8️⃣ Verify Deployment
        stage('8. Verify') {
            steps {
                bat 'kubectl get pods'
                bat 'kubectl get svc python-app-service'
                echo 'Deployment verified'
            }
        }
    }

    post {
        always {
            bat "docker rmi %DOCKER_IMAGE%:%DOCKER_TAG% || exit 0"
        }
        success {
            echo "SUCCESS - ${env.INACTIVE_SLOT} is now LIVE 🚀"
        }
        failure {
            echo "FAILED - deployment issue"
        }
    }
}

#!/bin/bash
#对镜象中的aws cli 升级
#报错退出
set -e

function before_script() {
    amazon-linux-extras install docker
    export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
    export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
    export AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION
}

function build_image(){
  local ecr_addr=$AWS_ECR_ADDRESS
  #登录aws 客户端
  aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ecr_addr

  time=$(date "+%Y-%m-%d")
  local image_name="${CI_COMMIT_REF_NAME}-${CI_PIPELINE_ID}"
  if [ ! -z "$CI_BUILD_TAG" ];then
    image_name=${CI_BUILD_TAG}
  fi

  local image_tag="${ecr_addr}/${CI_PROJECT_PATH}:${image_name}"

  echo "##########################build image start #####################"
  docker build -t $image_tag .
  echo "##########################build image end #####################"

  echo "##########################create ecr start #####################"
  local repository="aws ecr create-repository --repository-name ${CI_PROJECT_PATH} --region ${AWS_DEFAULT_REGION}"
  echo "create repository command "$repository
  echo "##########################create ecr end #####################"

 echo "##########################grype scan start #####################"
  # grype $image_tag
   # 设置出现什么级别漏洞报错，ci流程脚本会停止
  #grype $image_tag --fail-on medium or --fail-on critical
  echo "##########################grype scan end #####################"

  echo "##########################push image start #####################"
  local push="docker push ${image_tag}"
  echo "push command "$push
  eval $push || ($repository && $push)
  echo "##########################push image end #####################"

  echo "##########################remove local image start #####################"
  docker rmi $image_tag || true
  echo "##########################remove local image end #####################"
}

before_script
build_image

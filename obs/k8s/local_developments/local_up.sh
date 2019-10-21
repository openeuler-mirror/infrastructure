#!/usr/bin/env bash

# Copyright 2019 The Knative Authors.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


set -o errexit
set -o nounset
set -o pipefail

export CURRENT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/..

function check-prerequisites {
  echo "checking prerequisites....."
  echo "checking go environment"
  if hash go 2>/dev/null; then
    echo -n "found go, " && go version
  else
    echo "go not installed, exiting."
    exit 1
  fi

  if [[ "${GOPATH}" == "" ]]; then
    echo "GOPATH not set, exiting."
    exit 1
  fi

  echo "checking kubectl"
  if hash kubectl 2>/dev/null; then
    echo -n "found kubectl, " && kubectl version --short --client
  else
    echo "kubectl not installed, exiting."
    exit 1
  fi

  echo "checking docker"
  if hash docker 2>/dev/null; then
    echo -n "found docker, version: " && docker version
  else
     echo "docker not installed, exiting."
    exit 1
  fi

  echo "checking kind"
  if hash kind 2>/dev/null; then
    echo -n "found kind, version: " && kind version
  else
    echo "installing kind ."
    GO111MODULE="on" go get sigs.k8s.io/kind@v0.4.0
    export PATH=${GOPATH}/bin:${GOROOT}/bin:${PATH}
  fi
}

function kind-cluster-up {
    echo "Installing kind cluster named with integration...."
    kind create cluster --config "${CURRENT_DIR}/local_developments/kind-config.yaml" --name "integration"  --wait "200s"
}


echo "Preparing environment for obs basic environment"

check-prerequisites

kind-cluster-up

export KUBECONFIG="$(kind get kubeconfig-path --name='integration')"

kubectl apply -f "${CURRENT_DIR}/local_developments/all-in-one.yaml"

echo "all required services has been running up....
[k8s config]: export KUBECONFIG=\"$(kind get kubeconfig-path --name=integration)\""


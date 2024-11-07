#!/usr/bin/python3

import json
import subprocess

kubectl_path = "/usr/local/bin/kubectl"
pod_name = "ingress-nginx-ingress-nginx-controller-blah-blah"
namespace = "ingress-nginx"


def run_kubectl_command(command):
    base_cmd = f"{kubectl_path} exec -n {namespace} --stdin --tty {pod_name} --"
    full_cmd = f"{base_cmd} {command}"

    result = subprocess.run(full_cmd.split(), capture_output=True, text=True)
    return result.stdout


def get_nginx_config():
    return run_kubectl_command("/dbg conf")


def get_backend_config():
    return json.loads(run_kubectl_command("/dbg backends all"))


if __name__ == "__main__":
    nginx_config = get_nginx_config()
    backend_config = get_backend_config()

    backends = {backend["name"]: backend["endpoints"] for backend in backend_config}

    sites = {}
    current_server_name = None

    for line in nginx_config.splitlines():
        line = line.strip()

        if line.startswith("server_name "):
            current_server_name = line.split()[1]
        elif line.startswith('set $proxy_upstream_name "'):
            upstream_name = line.split()[-1].strip('";')

            if upstream_name not in ("-", "internal"):
                sites[current_server_name] = {
                    "label": upstream_name,
                    "endpoints": backends[upstream_name],
                }

    print(json.dumps(sites, indent=3, sort_keys=True))

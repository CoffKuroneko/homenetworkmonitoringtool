import subprocess

def run_traceroute(host):
    result = subprocess.run(
        ["traceroute", host],
        capture_output=True,
        text=True
    )
    return print(result.stdout)

run_traceroute("1.1.1.1")
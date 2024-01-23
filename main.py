import shlex
import subprocess
from concurrent.futures.thread import ThreadPoolExecutor

if __name__ == '__main__':
    with open('command.txt') as f:
        commands = f.readlines()
    with ThreadPoolExecutor(max_workers=5) as tpe:
        tpe.map(lambda i: subprocess.check_call(shlex.split(i)), commands)

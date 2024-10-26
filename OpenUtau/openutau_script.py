# import pexpect
# from abc import ABC, abstractmethod

# class CLIBase(ABC):
#     def __init__(self, command):
#         """Initialize an interactive CLI session."""
#         self.command = command
#         self.session = None
#         self.operations = []
    
#     def start_session(self):
#         """Start a new session."""
#         self.session = pexpect.spawn(self.command, encoding='utf-8')

#     def expect(self, pattern='>', timeout=30):
#         """Wait for a specific output pattern (prompt) in the session."""
#         try:
#             self.session.expect(pattern, timeout=timeout)
#         except pexpect.TIMEOUT:
#             raise TimeoutError(f"Pattern '{pattern}' not found within {timeout} seconds.")

#     def send(self, command):
#         """Send a command to the interactive session."""
#         self.session.sendline(command)

#     def get_output(self):
#         """Retrieve all output available up to this point in the session."""
#         return self.session.before.strip()

#     def execute_operations(self):
#         """Execute all queued operations in sequence and return results."""
#         results = []
#         for command in self.operations:
#             self.send(command)
#             self.expect()
#             results.append(self.get_output())
#         self.operations.clear()
#         return results
    
#     def close_session(self):
#         """Close the interactive session."""
#         if self.session and self.session.isalive():
#             self.session.terminate()
    
#     @abstractmethod
#     def queue_operation(self, operation, **kwargs):
#         """Queue a command for execution, to be implemented by subclasses."""
#         pass

# class OpenUtauCLI(CLIBase):
#     def __init__(self, command='OpenUtauCLI'):
#         """Initialize the OpenUtau CLI with specific command mappings."""
#         super().__init__(command)
#         self.command_map = {
#             "init": "--init",
#             "import_midi": "--import --midi {path}",
#             "set_lyrics": "--lyrics {path}",
#             "list_tracks": "--track --list",
#             "remove_track": "--track --remove",
#             "update_track": "--track --update",
#             "export_wav": "--export --wav"
#         }

#     def queue_operation(self, operation, **kwargs):
#         """Queue an OpenUtau-specific command based on the command map."""
#         if operation in self.command_map:
#             command = self.command_map[operation].format(**kwargs)
#             self.operations.append(command)
#         else:
#             raise ValueError(f"Operation '{operation}' not supported.")

#     def run(self):
#         """Run all queued operations in a new session."""
#         self.start_session()
#         try:
#             results = self.execute_operations()
#         finally:
#             self.close_session()
#         return results

# # Example usage:
# openutau = OpenUtauCLI('.\OpenUtau.exe --init')  # Replace with actual command path if needed
# openutau.queue_operation("init")
# openutau.queue_operation("import_midi", path="C:\\Users\\divan\\Downloads\\simple_midi.mid")
# openutau.queue_operation("set_lyrics", path="C:\\Users\\divan\\OneDrive\\Desktop\\AEOS\\simple_lyrics.txt")
# openutau.queue_operation("list_tracks")
# results = openutau.run()
# print("Operation Results:", results)


# version 2 :

# import subprocess
# from abc import ABC, abstractmethod

# class CLIBase(ABC):
#     def __init__(self, command):
#         """Initialize the CLI command for subprocess."""
#         self.command = command
#         self.operations = []
    
#     def execute_operations(self):
#         """Execute all queued operations in sequence and return results."""
#         results = []
#         for operation in self.operations:
#             full_command = f"{self.command} {operation}"
#             process = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#             stdout, stderr = process.communicate()
#             if stderr:
#                 results.append(f"Error: {stderr.strip()}")
#             else:
#                 results.append(stdout.strip())
#         self.operations.clear()
#         return results

#     @abstractmethod
#     def queue_operation(self, operation, **kwargs):
#         """Queue a command for execution, to be implemented by subclasses."""
#         pass

# class OpenUtauCLI(CLIBase):
#     def __init__(self, command='OpenUtauCLI'):
#         """Initialize the OpenUtau CLI with specific command mappings."""
#         super().__init__(command)
#         self.command_map = {
#             "init": "--init",
#             "import_midi": "--import --midi {path}",
#             "set_lyrics": "--lyrics {path}",
#             "list_tracks": "--track --list",
#             "remove_track": "--track --remove",
#             "update_track": "--track --update",
#             "export_wav": "--export --wav"
#         }

#     def queue_operation(self, operation, **kwargs):
#         """Queue an OpenUtau-specific command based on the command map."""
#         if operation in self.command_map:
#             command = self.command_map[operation].format(**kwargs)
#             self.operations.append(command)
#         else:
#             raise ValueError(f"Operation '{operation}' not supported.")

#     def run(self):
#         """Run all queued operations."""
#         return self.execute_operations()

# # Example usage:
# openutau = OpenUtauCLI('.\OpenUtau.exe')  # Replace with actual command path if needed
# openutau.queue_operation("init")
# openutau.queue_operation("import_midi", path="C:\\Users\\divan\\Downloads\\simple_midi.mid")
# openutau.queue_operation("set_lyrics", path="C:\\Users\\divan\\OneDrive\\Desktop\\AEOS\\simple_lyrics.txt")
# openutau.queue_operation("list_tracks")
# results = openutau.run()
# print("Operation Results:", results)


# version 3 :


# import subprocess
# from abc import ABC, abstractmethod

# class CLIBase(ABC):
#     def __init__(self, command):
#         """Initialize the CLI command for subprocess."""
#         self.command = command
#         self.operations = []
#         print(f"[INFO] CLI initialized with command: {self.command}")

#     def execute_operations(self):
#         """Execute all queued operations in sequence and return results."""
#         results = []
#         for idx, operation in enumerate(self.operations, start=1):
#             full_command = f"{self.command} {operation}"
#             print(f"[INFO] Executing operation {idx}/{len(self.operations)}: {full_command}")
#             process = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#             stdout, stderr = process.communicate()

#             if stderr:
#                 error_message = f"[ERROR] Operation failed: {stderr.strip()}"
#                 print(error_message)
#                 results.append(error_message)
#             else:
#                 success_message = f"[SUCCESS] Operation completed: {stdout.strip()}"
#                 print(success_message)
#                 results.append(stdout.strip())

#         self.operations.clear()
#         return results

#     @abstractmethod
#     def queue_operation(self, operation, **kwargs):
#         """Queue a command for execution, to be implemented by subclasses."""
#         pass

# class OpenUtauCLI(CLIBase):
#     def __init__(self, command='./OpenUtau.exe'):
#         """Initialize the OpenUtau CLI with specific command mappings."""
#         super().__init__(command)
#         self.command_map = {
#             "init": "--init",
#             "import_midi": "--import --midi {path}",
#             "set_lyrics": "--lyrics {path}",
#             "list_tracks": "--track --list",
#             "remove_track": "--track --remove",
#             "update_track": "--track --update",
#             "export_wav": "--export --wav"
#         }

#     def queue_operation(self, operation, **kwargs):
#         """Queue an OpenUtau-specific command based on the command map."""
#         if operation in self.command_map:
#             command = self.command_map[operation].format(**kwargs)
#             print(f"[INFO] Queued operation: {operation} -> {command}")
#             self.operations.append(command)
#         else:
#             raise ValueError(f"[ERROR] Operation '{operation}' not supported.")

#     def run(self):
#         """Run all queued operations."""
#         print("[INFO] Starting execution of all queued operations.")
#         results = self.execute_operations()
#         print("[INFO] All operations executed.")
#         return results

# # Example usage:
# openutau = OpenUtauCLI('OpenUtau.exe')
# openutau.queue_operation("init")
# openutau.queue_operation("import_midi", path="C:\\Users\\divan\\Downloads\\simple_midi.mid")
# openutau.queue_operation("set_lyrics", path="C:\\Users\\divan\\OneDrive\\Desktop\\AEOS\\simple_lyrics.txt")
# openutau.queue_operation("list_tracks")
# results = openutau.run()
# print("\nFinal Results of All Operations:")
# for result in results:
#     print(result)


# version 4 :

import subprocess
from abc import ABC, abstractmethod

class CLIBase(ABC):
    def __init__(self, command):
        """Initialize the CLI command for subprocess."""
        self.command = command
        self.operations = []
        print(f"[INFO] CLI initialized with command: {self.command}")

    def execute_operations(self, timeout=10):
        """Execute all queued operations in sequence with real-time output."""
        results = []
        for idx, operation in enumerate(self.operations, start=1):
            full_command = f"{self.command} {operation}"
            print(f"[INFO] Executing operation {idx}/{len(self.operations)}: {full_command}")
            try:
                # Run command with real-time stdout and stderr capture
                process = subprocess.Popen(
                    full_command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Stream output line by line
                stdout_lines = []
                stderr_lines = []
                for line in process.stdout:
                    print(f"[STDOUT] {line.strip()}")
                    stdout_lines.append(line.strip())

                for line in process.stderr:
                    print(f"[STDERR] {line.strip()}")
                    stderr_lines.append(line.strip())

                process.wait(timeout=timeout)  # Timeout to prevent hanging

                # Check the final state of stdout and stderr
                if process.returncode == 0:
                    result_message = f"[SUCCESS] Operation {idx} completed: {' '.join(stdout_lines)}"
                    print(result_message)
                    results.append(result_message)
                else:
                    error_message = f"[ERROR] Operation {idx} failed: {' '.join(stderr_lines)}"
                    print(error_message)
                    results.append(error_message)

            except subprocess.TimeoutExpired:
                error_message = f"[TIMEOUT] Operation {idx} timed out after {timeout} seconds."
                print(error_message)
                process.kill()
                results.append(error_message)
            except Exception as e:
                error_message = f"[ERROR] Unexpected error: {e}"
                print(error_message)
                process.kill()
                results.append(error_message)

        self.operations.clear()
        return results

    @abstractmethod
    def queue_operation(self, operation, **kwargs):
        """Queue a command for execution, to be implemented by subclasses."""
        pass

class OpenUtauCLI(CLIBase):
    def __init__(self, command='OpenUtau.exe'):
        """Initialize the OpenUtau CLI with specific command mappings."""
        super().__init__(command)
        self.command_map = {
            "init": "--init",
            "import_midi": "--import --midi {path}",
            "set_lyrics": "--lyrics {path}",
            "list_tracks": "--track --list",
            "remove_track": "--track --remove",
            "update_track": "--track --update",
            "export_wav": "--export --wav"
        }

    def queue_operation(self, operation, **kwargs):
        """Queue an OpenUtau-specific command based on the command map."""
        if operation in self.command_map:
            command = self.command_map[operation].format(**kwargs)
            print(f"[INFO] Queued operation: {operation} -> {command}")
            self.operations.append(command)
        else:
            raise ValueError(f"[ERROR] Operation '{operation}' not supported.")

    def run(self, timeout=10):
        """Run all queued operations with timeout management."""
        print("[INFO] Starting execution of all queued operations.")
        results = self.execute_operations(timeout=timeout)
        print("[INFO] All operations executed.")
        return results

# Example usage:
openutau = OpenUtauCLI('OpenUtau.exe')
openutau.queue_operation("init")
openutau.queue_operation("import_midi", path="C:\\Users\\divan\\Downloads\\simple_midi.mid")
openutau.queue_operation("set_lyrics", path="C:\\Users\\divan\\OneDrive\\Desktop\\AEOS\\simple_lyrics.txt")
openutau.queue_operation("list_tracks")
results = openutau.run(timeout=10)
print("\nFinal Results of All Operations:")
for result in results:
    print(result)
"""Python code execution in isolated Docker sandbox."""
import docker
from ..base import BaseTool, ToolInfo
from logger_utils import get_logger
import sys


class PythonSandboxTool(BaseTool):
    """
    Execute Python code in a secure Docker sandbox.
    
    Features:
    - Resource limits (256MB memory, limited CPU)
    - Automatic container cleanup
    - Safe code execution
    """
    
    def __init__(self):
        """Initialize PythonSandboxTool."""
        info = ToolInfo(
            name="python_sandbox",
            description="Execute Python code in a secure Docker sandbox. Returns stdout output only.",
            enabled=True,
            needs_confirmation=True,  # Always confirm before running code
            timeout=30
        )
        super().__init__(info)
        try:
            self.docker_client = docker.from_env()
            self.logger.info("PythonSandboxTool initialized, Docker client connected")
        except Exception as e:
            self.logger.error(f"Failed to connect to Docker: {e}")
            self.docker_client = None
    
    def validate_arguments(self, **kwargs) -> tuple[bool, str]:
        """
        Validate sandbox arguments.
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        code = kwargs.get("code")
        
        if not code:
            return False, "Missing required argument: code"
        
        if not isinstance(code, str):
            return False, "code must be a string"
        
        if not self.docker_client:
            return False, "Docker connection not available"
        
        return True, ""
    
    def execute(self, **kwargs) -> str:
        """Execute Python code in sandbox."""
        code = kwargs.get("code")
        
        try:
            self.logger.info("Executing Python code in sandbox...")
            self.logger.debug(f"Code:\n{code}")
            
            container_output = self.docker_client.containers.run(
                image="ai-sandbox",
                command=['python3', '-c', code],
                network_mode="bridge",
                mem_limit="256m",
                cpu_quota=50000,
                remove=True,
                stdout=True,
                stderr=True,
                detach=False
            )
            
            if isinstance(container_output, bytes):
                result = container_output.decode('utf-8').strip()
            else:
                result = str(container_output).strip()
            
            if not result:
                warning_msg = (
                    "[Warning: Code executed but returned empty output. "
                    "Make sure to use print() to output results.]"
                )
                self.logger.warning("Sandbox returned empty output")
                sys.stdout.write(f"\r⚠️  {warning_msg}\n")
                return warning_msg
            
            self.logger.info(f"✓ Code execution successful. Output: {result[:100]}")
            sys.stdout.write(f"\r📊 Sandbox result: {result}\n")
            return result
        
        except docker.errors.ContainerError as e:
            stderr = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else str(e.stderr)
            stdout = e.stdout.decode('utf-8') if isinstance(e.stdout, bytes) else str(e.stdout)
            
            error_msg = f"❌ Code execution error:\nStdout: {stdout}\nStderr: {stderr}"
            self.logger.error(error_msg)
            print(error_msg)
            return error_msg
        
        except docker.errors.ImageNotFound:
            error_msg = (
                "❌ Docker image 'ai-sandbox' not found.\n"
                "Please build it first: docker build -t ai-sandbox ."
            )
            self.logger.error(error_msg)
            print(error_msg)
            return error_msg
        
        except docker.errors.APIError as e:
            error_msg = f"❌ Docker API error: {str(e)}"
            self.logger.error(error_msg)
            print(error_msg)
            return error_msg
        
        except Exception as e:
            error_msg = f"❌ Sandbox execution failed: {str(e)}\nType: {type(e).__name__}"
            self.logger.error(error_msg)
            print(error_msg)
            return error_msg
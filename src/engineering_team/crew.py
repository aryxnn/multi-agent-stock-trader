import os
# pyrefly: ignore [missing-import]
from crewai import Agent, Crew, Process, Task
# pyrefly: ignore [missing-import]
from crewai.project import CrewBase, agent, crew, task
# pyrefly: ignore [missing-import]
from crewai.tasks.task_output import TaskOutput

@CrewBase
class EngineeringTeam():
    """EngineeringTeam crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @staticmethod
    def clean_markdown_callback(task_output: TaskOutput):
        """Callback to strip markdown code blocks from output files in the output directory."""
        output_dir = "output"
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                filepath = os.path.join(output_dir, filename)
                if os.path.isfile(filepath) and (filename.endswith(".py") or filename.endswith(".txt") or filename == "Dockerfile"):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        
                        modified = False
                        # Strip leading markdown wrappers
                        if content.startswith("```python"):
                            content = content[len("```python"):].strip()
                            modified = True
                        elif content.startswith("```"):
                            content = content[3:].strip()
                            modified = True
                        
                        # Strip trailing markdown wrappers
                        if content.endswith("```"):
                            content = content[:-3].strip()
                            modified = True
                        
                        if modified:
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(content)
                            print(f"[Callback] Cleaned markdown wrappers from {filepath}")
                    except Exception as e:
                        print(f"Error cleaning {filepath}: {e}")

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'],
            verbose=True,
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=500, 
            max_retry_limit=3 
        )
    
    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            verbose=True,
        )

    @agent
    def security_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['security_engineer'],
            verbose=True,
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",  # Using Docker for safety
            max_execution_time=500, 
            max_retry_limit=3 
        )

    @agent
    def devops_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['devops_engineer'],
            verbose=True,
        )    

    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task']
        )

    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_task'],
            callback=self.clean_markdown_callback
        )

    @task
    def security_audit_task(self) -> Task:
        return Task(
            config=self.tasks_config['security_audit_task'],
        )    

    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_task'],
            callback=self.clean_markdown_callback
        )

    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_task'],
            callback=self.clean_markdown_callback
        )    
    
    
    def refine_code_task(self) -> Task:
        return Task(
            config=self.tasks_config['refine_code_task'],
            agent=self.backend_engineer(),  # Explicitly bind the agent object
            callback=self.clean_markdown_callback
        )    

    def refine_frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['refine_frontend_task'],
            agent=self.frontend_engineer(),  # Explicitly bind the agent object
            callback=self.clean_markdown_callback
        )    

    @task
    def generate_requirements_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_requirements_task'],
            callback=self.clean_markdown_callback
        )

    @task
    def generate_dockerfile_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_dockerfile_task'],
            callback=self.clean_markdown_callback
        )    

    @crew
    def crew(self) -> Crew:
        """Creates the research crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
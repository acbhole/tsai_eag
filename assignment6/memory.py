class Memory:
    def __init__(self):
        self.iteration = 0
        self.max_iterations = 9
        self.last_response = None
        self.iteration_responses = []
        self.preferences = {}

    def update_iteration(self):
        self.iteration += 1

    # def add_response(self, response):
    #     self.last_response = response
    #     self.iteration_responses.append(response)

    def add_response(self, iteration, tool_name, tool_input, result):
        """Add a structured response to memory."""
        self.iteration_responses.append({
            "iteration": iteration,
            "tool": tool_name,
            "input": tool_input,
            "output": result
        })

    def get_history(self):
        """Generate a formatted history string from structured responses."""
        if not self.iteration_responses:
            return ""
        history = "Previous steps:\n"
        for resp in self.iteration_responses:
            iteration = resp["iteration"]
            tool = resp["tool"]
            input_str = str(resp["input"])
            output_str = str(resp["output"])
            history += f"{iteration}. Called {tool} with {input_str}, got {output_str}\n"
        return history


    # add function to get last added response from memory
    def get_last_response(self):
        """Get the last added response."""
        if self.iteration_responses:
            return self.iteration_responses[-1]
        return None

    # def update_iteration(self):
    #     """Increment the iteration counter."""
    #     self.iteration += 1

    # def get_history(self):
    #     return " ".join(self.iteration_responses)
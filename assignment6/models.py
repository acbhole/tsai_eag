from typing import List, Union

from pydantic import BaseModel, Field


class ToolModel(BaseModel):
    @classmethod
    def as_tool(cls):
        return {
            "name": cls.__name__,
            "description": cls.__doc__,
            "inputSchema": cls.model_json_schema(),
        }

    def __str__(self):
        tool = self.as_tool()
        return str(tool)


class ASCIIInput(ToolModel):
    string: str = Field(..., description="The input string to convert to ASCII values.")


class ASCIIOutput(ToolModel):
    ascii_values: List[int] = Field(
        ..., description="The ASCII values of the input string."
    )


class ExponentialInput(ToolModel):
    int_list: List[int] = Field(
        ..., description="A list of integers to calculate the sum of exponentials."
    )


class ExponentialOutput(ToolModel):
    sum_exponentials: float = Field(
        ..., description="The sum of exponentials of the input integers."
    )


class PaintOutput(ToolModel):
    message: str = Field(
        ..., description="A message indicating the success or failure of the operation."
    )


class RectangleInput(ToolModel):
    x1: int = Field(..., description="The x-coordinate of the starting point.")
    y1: int = Field(..., description="The y-coordinate of the starting point.")
    x2: int = Field(..., description="The x-coordinate of the ending point.")
    y2: int = Field(..., description="The y-coordinate of the ending point.")


class TextInput(ToolModel):
    text: str = Field(..., description="The text to be added to the canvas.")


class EmailInput(ToolModel):
    recipient_email: str = Field(..., alias="to", alias_priority=2, description="The recipient email address.")
    subject: str = Field(..., description="The subject of the email.")
    body: str = Field(..., description="The content of the email.")

class TelegramInput(ToolModel):
    chat_id: Union[str, int] = Field(
        ...,
        description="The chat ID to send the message to",
        examples=["123456789", 987654321],
        type="string",	

    )
    message: str = Field(
        ...,
        description="The message to be sent.",
    )
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "chat_id": "123456789",
                    "message": "Hello!"
                }
            ]
        }
        json_encoders = {
            int: str  # convert integers to strings for chat_id
        }



class FibonacciInput(BaseModel):
    n: int = Field(..., description="The number of Fibonacci numbers to generate.")


class FibonacciOutput(BaseModel):
    fibonacci_numbers: List[int] = Field(
        ..., description="The list of Fibonacci numbers."
    )


class CubeInput(BaseModel):
    numbers: List[int] = Field(
        ..., description="The list of numbers to calculate cubes for."
    )


class CubeOutput(BaseModel):
    cubes: List[int] = Field(..., description="The list of cubes of the input numbers.")

class SquareInput(BaseModel):
    numbers: List[int] = Field(
        ..., description="The list of numbers to calculate squares for."
    )

class SquareOutput(BaseModel):
    squares: List[int] = Field(..., description="The list of squares of the input numbers.")    


class SumInput(BaseModel):
    numbers: List[int] = Field(
        ..., description="The list of numbers to calculate the sum for."
    )


class SumOutput(BaseModel):
    total: int = Field(..., description="The sum of the input numbers.")



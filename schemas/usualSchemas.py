from pydantic import BaseModel

class AddChannelRequestSchema(BaseModel):
    channel_type: str
    channel_list: list
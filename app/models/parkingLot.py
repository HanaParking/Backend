from pydantic import BaseModel, ConfigDict

class parkingSpotOut(BaseModel):
    lot_code : str
    spot_row : int
    spot_column : int
    occupied_cd : str
    model_config = ConfigDict(from_attributes=True)
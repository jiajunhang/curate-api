class Item(BaseModel):
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    index: int
    question: str
    options: List[str]
    correct: int
    difficulty: float

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data["_id"] is None:
            data.pop("_id")
        return data
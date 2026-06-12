class Ship:
  
  def __init__(self, size: int, coordinates: list[tuple[int, int]]):
    self.size = size
    self.coordinates = coordinates
    self.hits = set()


  def hit(self, coord):
    if coord in self.coordinates:
      self.hits.add(coord)


  def is_sunk(self):
    return len(self.hits) == self.size
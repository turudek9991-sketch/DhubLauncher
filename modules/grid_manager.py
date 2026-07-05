class GridManager:
    def __init__(self, grid_config: dict = None):
        self.grid_config = grid_config or {
            "start_x_base": 660,
            "window_width": 180,
            "window_height": 100,
            "columns": 2,
            "top_margin": 60,
            "gap": 5
        }

    def calculate_xml_coordinates(self, index: int) -> dict:
        """Menghitung koordinat Rectangle (Left, Top, Right, Bottom) berdasarkan konfigurasi grid compact."""
        cfg = self.grid_config
        row = index // cfg["columns"]
        col = index % cfg["columns"]

        left = cfg["start_x_base"] + (col * (cfg["window_width"] + cfg["gap"]))
        top = cfg["top_margin"] + (row * (cfg["window_height"] + cfg["gap"]))
        right = left + cfg["window_width"]
        bottom = top + cfg["window_height"]

        return {"left": left, "top": top, "right": right, "bottom": bottom}

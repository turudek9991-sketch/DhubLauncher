class GridManager:
    def __init__(self, config_mgr):
        self.config_mgr = config_mgr

    def get_coordinates(self, index):
        """
        Menghitung koordinat Rectangle (Left, Top, Right, Bottom) 
        berdasarkan konfigurasi grid dinamis dari config_mgr.
        """
        c = self.config_mgr.config_data
        
        # Ambil parameter dari config (dengan nilai default yang aman)
        cols = c.get("grid_columns", 2)
        start_x = c.get("grid_start_x", 660)
        width = c.get("grid_width", 280)
        height = c.get("grid_height", 200)
        gap = c.get("grid_gap", 5)
        top_margin = c.get("grid_top_margin", 60)
        
        # Logika pembagian grid
        row = index // cols
        col = index % cols
        
        left = start_x + (col * (width + gap))
        top = top_margin + (row * (height + gap))
        
        return {
            "left": left,
            "top": top,
            "right": left + width,
            "bottom": top + height
        }

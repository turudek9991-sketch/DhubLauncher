import os
import xml.etree.ElementTree as ET

class XMLManager:
    def __init__(self, process_manager, logger):
        self.proc = process_manager
        self.logger = logger
        self.local_home = "/data/data/com.termux/files/home"

    def inject(self, pkg_name, coords):
        """
        Suntikkan koordinat grid ke XML preferensi App Cloner.
        Menggunakan temp file di home Termux untuk menghindari Read-only FS.
        """
        remote = f"/data/user/0/{pkg_name}/shared_prefs/{pkg_name}_preferences.xml"
        local = f"{self.local_home}/{pkg_name}_prefs.xml"
        
        # Ambil file dari root
        self.proc.run(f"cp {remote} {local}")
        self.proc.run(f"chmod 777 {local}")
        
        if not os.path.exists(local) or os.path.getsize(local) == 0:
            self.logger.error(f"Gagal akses XML: {pkg_name}")
            return False
            
        try:
            tree = ET.parse(local)
            root = tree.getroot()
            target = {
                "app_cloner_current_window_left": str(coords["left"]),
                "app_cloner_current_window_top": str(coords["top"]),
                "app_cloner_current_window_right": str(coords["right"]),
                "app_cloner_current_window_bottom": str(coords["bottom"])
            }
            
            for k, v in target.items():
                found = False
                for elem in root.findall("int"):
                    if elem.get("name") == k:
                        elem.set("value", v)
                        found = True; break
                if not found: ET.SubElement(root, "int", name=k, value=v)
            
            tree.write(local, encoding="utf-8", xml_declaration=True)
            
            # Kembalikan ke root
            self.proc.run(f"cp {local} {remote}")
            self.proc.run(f"chmod 660 {remote}")
            if os.path.exists(local): os.remove(local)
            return True
        except Exception as e:
            self.logger.error(f"XML Injection Error pada {pkg_name}: {e}")
            return False

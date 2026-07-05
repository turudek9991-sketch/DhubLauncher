import os
import xml.etree.ElementTree as ET


class XMLManager:
    def __init__(self, process_manager):
        self.proc = process_manager

    def inject(self, package: str, coordinate: dict) -> bool:
        """Modifikasi file preferensi XML App Cloner dengan memanfaatkan buffer home internal Termux."""
        remote_xml_path = f"/data/user/0/{package}/shared_prefs/{package}_preferences.xml"
        local_home = "/data/data/com.termux/files/home"
        local_temp_path = f"{local_home}/{package}_prefs.xml"

        self.proc.run(f"cp {remote_xml_path} {local_temp_path}")
        self.proc.run(f"chmod 777 {local_temp_path}")

        if not os.path.exists(local_temp_path) or os.path.getsize(local_temp_path) == 0:
            return False

        try:
            tree = ET.parse(local_temp_path)
            root = tree.getroot()

            target_keys = {
                "app_cloner_current_window_left": str(coordinate["left"]),
                "app_cloner_current_window_top": str(coordinate["top"]),
                "app_cloner_current_window_right": str(coordinate["right"]),
                "app_cloner_current_window_bottom": str(coordinate["bottom"])
            }

            for key, value in target_keys.items():
                found = False
                for elem in root.findall("int"):
                    if elem.get("name") == key:
                        elem.set("value", value)
                        found = True
                        break
                if not found:
                    ET.SubElement(root, "int", name=key, value=value)

            tree.write(local_temp_path, encoding="utf-8", xml_declaration=True)

            self.proc.run(f"cp {local_temp_path} {remote_xml_path}")
            self.proc.run(f"chmod 660 {remote_xml_path}")

            if os.path.exists(local_temp_path):
                os.remove(local_temp_path)

            return True
        except Exception:
            return False

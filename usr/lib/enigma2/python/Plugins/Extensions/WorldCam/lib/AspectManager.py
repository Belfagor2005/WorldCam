

try:
	from Components.AVSwitch import AVSwitch
except ImportError:
	from Components.AVSwitch import eAVControl as AVSwitch


class AspectManager:
	def __init__(self):
		self.init_aspect = self.get_current_aspect()
		print("[INFO] Initial aspect ratio:", self.init_aspect)

	def get_current_aspect(self):
		"""Restituisce l'aspect ratio attuale del dispositivo."""
		try:
			return int(AVSwitch().getAspectRatioSetting())
		except Exception as e:
			print("[ERROR] Failed to get aspect ratio:", str(e))
			return 0  # Valore di default in caso di errore

	def restore_aspect(self):
		"""Ripristina l'aspect ratio originale all'uscita del plugin."""
		try:
			print("[INFO] Restoring aspect ratio to:", self.init_aspect)
			AVSwitch().setAspectRatio(self.init_aspect)
		except Exception as e:
			print("[ERROR] Failed to restore aspect ratio:", str(e))


aspect_manager = AspectManager()

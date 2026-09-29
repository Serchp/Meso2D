from .service_EN import (
	save_current_view,
	save_viewport_image,
)

save_current_view_bridge = save_current_view
save_viewport_image_bridge = save_viewport_image

__all__ = [
	"save_current_view",
	"save_current_view_bridge",
	"save_viewport_image",
	"save_viewport_image_bridge",
]

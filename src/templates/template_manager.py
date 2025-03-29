from typing import Dict, Optional
from pathlib import Path
import yaml
import jinja2
import logging

class TemplateManager:
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.logger = logging.getLogger(__name__)
        self.templates: Dict[str, Dict] = self._load_templates()
        
    def _load_templates(self) -> Dict[str, Dict]:
        """Load all template configurations."""
        templates = {}
        for config_file in self.templates_dir.glob("**/template.yaml"):
            try:
                config = yaml.safe_load(config_file.read_text())
                template_name = config_file.parent.name
                templates[template_name] = config
            except Exception as e:
                self.logger.error(f"Error loading template {config_file}: {str(e)}")
        return templates
    
    def get_template(self, name: str, framework: Optional[str] = None) -> Optional[str]:
        """Get a template by name and optionally framework."""
        if name not in self.templates:
            return None
            
        template_config = self.templates[name]
        
        # Get framework-specific template if available
        template_file = template_config.get("frameworks", {}).get(framework, 
                                          template_config["default"])
        
        try:
            template = self.env.get_template(template_file)
            return template
        except Exception as e:
            self.logger.error(f"Error loading template file {template_file}: {str(e)}")
            return None
    
    def render_template(self, 
                       name: str, 
                       context: Dict, 
                       framework: Optional[str] = None) -> Optional[str]:
        """Render a template with given context."""
        template = self.get_template(name, framework)
        if not template:
            return None
            
        try:
            return template.render(**context)
        except Exception as e:
            self.logger.error(f"Error rendering template {name}: {str(e)}")
            return None 
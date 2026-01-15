"""Auto-detect and monitor PokerStars hand history folder."""
import os
from pathlib import Path
from typing import List


class FileWatcher:
    """Watch for PokerStars hand history files."""
    
    def __init__(self, config):
        self.config = config
        self.pokerstars_paths = self._get_pokerstars_paths()
    
    def _get_pokerstars_paths(self) -> List[Path]:
        """Get possible PokerStars hand history locations."""
        home = Path.home()
        
        # MacOS paths
        mac_paths = [
            home / 'Library' / 'Application Support' / 'PokerStars' / 'HandHistory',
            home / 'Library' / 'Application Support' / 'PokerStarsEU' / 'HandHistory',
        ]
        
        # Also check manual folder
        manual_path = Path(self.config.get('hand_history_dir', 'hand_histories'))
        
        paths = [manual_path] + mac_paths
        return [p for p in paths if p.exists()]
    
    def scan_for_files(self) -> List[str]:
        """Scan all possible locations for hand history files."""
        all_files = []
        
        for base_path in self.pokerstars_paths:
            # Look for files in base path and subdirectories
            txt_files = list(base_path.rglob('*.txt'))
            all_files.extend([str(f) for f in txt_files])
        
        return all_files
    
    def get_detected_paths(self) -> List[str]:
        """Get list of detected PokerStars folders."""
        return [str(p) for p in self.pokerstars_paths]

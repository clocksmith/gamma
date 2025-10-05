"""
Simple GGUF metadata parser.

This is a lightweight parser that extracts basic metadata from GGUF files
without loading the entire model.
"""

import struct
import os
from typing import Dict, Any, Optional
from pathlib import Path


# GGUF magic number
GGUF_MAGIC = 0x46554747  # 'GGUF' in little-endian
GGUF_VERSION = 3


class GGUFMetadata:
    """Parse and store GGUF file metadata."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.metadata = {}
        self.valid = False

        if os.path.exists(file_path):
            self._parse()

    def _parse(self) -> None:
        """Parse GGUF file header and metadata."""
        try:
            with open(self.file_path, 'rb') as f:
                # Read magic number
                magic = struct.unpack('<I', f.read(4))[0]

                if magic != GGUF_MAGIC:
                    return

                # Read version
                version = struct.unpack('<I', f.read(4))[0]

                if version != GGUF_VERSION:
                    # Try to support older versions minimally
                    pass

                # Read tensor count and KV count
                tensor_count = struct.unpack('<Q', f.read(8))[0]
                kv_count = struct.unpack('<Q', f.read(8))[0]

                # For simplicity, we'll extract basic info from filename
                # and file size instead of parsing full KV metadata
                # (Full parsing requires reading variable-length strings and types)

                self.metadata['tensor_count'] = tensor_count
                self.metadata['kv_count'] = kv_count
                self.metadata['version'] = version

                self.valid = True

                # Extract info from filename (common patterns)
                self._parse_filename()

        except Exception as e:
            self.valid = False

    def _parse_filename(self) -> None:
        """Extract information from filename."""
        filename = os.path.basename(self.file_path).lower()

        # Common quantization patterns
        if 'q4_0' in filename:
            self.metadata['quantization'] = 'Q4_0'
        elif 'q4_1' in filename:
            self.metadata['quantization'] = 'Q4_1'
        elif 'q4_k_s' in filename or 'q4_k_small' in filename:
            self.metadata['quantization'] = 'Q4_K_S'
        elif 'q4_k_m' in filename or 'q4_k_medium' in filename:
            self.metadata['quantization'] = 'Q4_K_M'
        elif 'q5_0' in filename:
            self.metadata['quantization'] = 'Q5_0'
        elif 'q5_1' in filename:
            self.metadata['quantization'] = 'Q5_1'
        elif 'q5_k_s' in filename:
            self.metadata['quantization'] = 'Q5_K_S'
        elif 'q5_k_m' in filename:
            self.metadata['quantization'] = 'Q5_K_M'
        elif 'q6_k' in filename:
            self.metadata['quantization'] = 'Q6_K'
        elif 'q8_0' in filename:
            self.metadata['quantization'] = 'Q8_0'
        elif 'f16' in filename or 'fp16' in filename:
            self.metadata['quantization'] = 'F16'
        elif 'f32' in filename or 'fp32' in filename:
            self.metadata['quantization'] = 'F32'
        else:
            self.metadata['quantization'] = 'unknown'

        # Parameter count
        if '1b' in filename or '1.5b' in filename:
            self.metadata['param_billions'] = 1
        elif '2b' in filename or '2.5b' in filename:
            self.metadata['param_billions'] = 2
        elif '3b' in filename:
            self.metadata['param_billions'] = 3
        elif '4b' in filename:
            self.metadata['param_billions'] = 4
        elif '7b' in filename:
            self.metadata['param_billions'] = 7
        elif '8b' in filename:
            self.metadata['param_billions'] = 8
        elif '9b' in filename:
            self.metadata['param_billions'] = 9
        elif '12b' in filename or '13b' in filename:
            self.metadata['param_billions'] = 12
        elif '27b' in filename:
            self.metadata['param_billions'] = 27
        elif '33b' in filename:
            self.metadata['param_billions'] = 33
        elif '70b' in filename:
            self.metadata['param_billions'] = 70
        else:
            self.metadata['param_billions'] = None

        # Architecture detection
        if 'llama' in filename:
            self.metadata['architecture'] = 'llama'
        elif 'gemma' in filename:
            self.metadata['architecture'] = 'gemma'
        elif 'mistral' in filename:
            self.metadata['architecture'] = 'mistral'
        elif 'phi' in filename:
            self.metadata['architecture'] = 'phi'
        else:
            self.metadata['architecture'] = 'unknown'

    def get_file_size_mb(self) -> int:
        """Get file size in MB."""
        try:
            return os.path.getsize(self.file_path) // (1024 * 1024)
        except:
            return 0

    def get_file_size_gb(self) -> float:
        """Get file size in GB."""
        return self.get_file_size_mb() / 1024

    def get_architecture(self) -> str:
        """Get model architecture."""
        return self.metadata.get('architecture', 'unknown')

    def get_quantization(self) -> str:
        """Get quantization level."""
        return self.metadata.get('quantization', 'unknown')

    def get_param_count_billions(self) -> Optional[int]:
        """Get parameter count in billions."""
        return self.metadata.get('param_billions')

    def format_info(self) -> str:
        """Format metadata for display."""
        if not self.valid:
            return "Invalid GGUF file or unable to parse"

        lines = []
        lines.append(f"File: {os.path.basename(self.file_path)}")
        lines.append(f"Size: {self.get_file_size_gb():.2f}GB")

        if self.get_architecture() != 'unknown':
            lines.append(f"Architecture: {self.get_architecture()}")

        if self.get_param_count_billions():
            lines.append(f"Parameters: ~{self.get_param_count_billions()}B")

        if self.get_quantization() != 'unknown':
            lines.append(f"Quantization: {self.get_quantization()}")

        lines.append(f"Tensors: {self.metadata.get('tensor_count', 'unknown')}")

        return "\n".join(lines)

    def is_valid(self) -> bool:
        """Check if file was successfully parsed."""
        return self.valid


def parse_gguf_file(file_path: str) -> Optional[GGUFMetadata]:
    """
    Parse a GGUF file and return metadata.

    Args:
        file_path: Path to GGUF file

    Returns:
        GGUFMetadata object or None if invalid
    """
    metadata = GGUFMetadata(file_path)
    return metadata if metadata.is_valid() else None

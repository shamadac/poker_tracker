# Shared Directory

This directory contains shared resources between frontend and backend:

- `types/` - Shared TypeScript/Python type definitions
- `constants/` - Shared constants and enums
- `utils/` - Shared utility functions
- `uploads/` - Temporary file uploads (development only)
- `temp/` - Temporary processing files

## Usage

The shared directory is mounted in both frontend and backend containers to enable:
- Type sharing between TypeScript and Python
- Shared configuration files
- File exchange during development
- Common utilities and constants
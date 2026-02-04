## Summary

Brief description of changes.

## Changes

- [ ] Change 1
- [ ] Change 2

## Testing

- [ ] All existing tests pass (`python3 -m pytest tests/ -v`)
- [ ] New tests added for new functionality
- [ ] Shellcheck passes (`shellcheck scripts/*`)
- [ ] No `print()` or `sys.exit()` in `src/mac_sweep/core/`
- [ ] No `shell=True` in any subprocess call
- [ ] No `sudo` usage

## Security Checklist

- [ ] Input validation for any new user inputs
- [ ] No hardcoded credentials or API keys
- [ ] AppleScript paths properly escaped
- [ ] Package names validated before use in commands

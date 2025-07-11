# Changelog

All notable changes to AlteruPhono will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Critical**: Fixed version inconsistency between setup.py (0.6.0) and __init__.py (0.8.0)
- Established single source of truth for versioning in __init__.py
- Updated setup.py to automatically extract version from __init__.py

### Added
- Modern packaging with pyproject.toml following PEP 621 standards
- Comprehensive version consistency checker script
- GitHub Actions workflow for automated version consistency checking
- Modern CI/CD pipeline supporting Python 3.8-3.11 across multiple operating systems
- Development dependencies and optional dependency groups in pyproject.toml
- Automated test coverage reporting with codecov integration

### Changed
- Updated setup.py description to better reflect current capabilities
- Enhanced keywords in package metadata for better discoverability
- Modernized GitHub Actions workflows with latest action versions
- Updated Python version support matrix to 3.8-3.11 (dropped 3.7)

### Infrastructure
- Added automated version consistency validation
- Improved CI/CD pipeline with lint, test, and package validation jobs
- Added code formatting and type checking to CI pipeline
- Enhanced error handling in version extraction

## [0.8.0] - 2024-12-XX

### Added
- **Major**: Pluggable feature systems architecture
- **Major**: Tresoldi comprehensive feature system (1,081 sounds, 43 features)
- **Major**: Unified distinctive feature system with scalar values
- **Major**: Advanced sound change engine with gradient capabilities
- Enhanced Sound class with rich feature representations
- Cross-system feature conversion utilities
- Comprehensive test suite with 85.1% success rate on 801 sound change rules
- Performance optimizations (12.5x improvement in sound creation)
- Memory efficiency improvements (7-12x reduction in usage)

### Changed
- Transitioned from external maniphono dependency to internal phonology module
- Improved parsing system with better error handling
- Enhanced prosodic hierarchy support (Phase 4)

### Fixed
- Multiple bug fixes in sound change rule application
- Improved feature arithmetic and value handling
- Better syllabification algorithms
- Enhanced environment matching for cross-system compatibility

## [0.7.0] - Previous Release

### Added
- Enhanced parsing system with AST-based approach
- Improved error handling and validation
- Extended rule syntax support

## [0.6.0] - Previous Release

### Added
- Basic sound change modeling capabilities
- Core parsing infrastructure
- Initial feature system support

---

## Version History Summary

- **0.8.0**: Major feature systems overhaul with comprehensive phonological coverage
- **0.7.0**: Enhanced parsing and validation systems
- **0.6.0**: Core sound change modeling foundation

## Migration Guide

### From 0.6.0 to 0.8.0

The 0.8.0 release introduces significant new capabilities while maintaining backward compatibility for core functionality:

#### New Features Available
- Use the new feature systems: `get_feature_system('tresoldi_distinctive')`
- Enhanced Sound class: `from alteruphono.phonology.sound_v2 import Sound`
- Advanced sound change engine: `from alteruphono.phonology.sound_change import SoundChangeEngine`

#### Deprecated (but still supported)
- Basic sound change syntax continues to work as before
- Core API functions (`forward`, `backward`) remain unchanged

#### Breaking Changes
- None for core API - fully backward compatible

## Development and Contribution

### Version Management
- Version is defined in `alteruphono/__init__.py` as the single source of truth
- `setup.py` automatically extracts version to maintain consistency
- `pyproject.toml` uses dynamic versioning
- Version consistency is validated in CI/CD pipeline

### Release Process
1. Update version in `alteruphono/__init__.py`
2. Update CHANGELOG.md with release notes
3. Run `python scripts/check_version_consistency.py` to verify consistency
4. Create release tag and GitHub release
5. Automated CI/CD will handle package building and publishing

For development setup and contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).
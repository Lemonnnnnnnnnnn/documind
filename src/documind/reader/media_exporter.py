"""Export embedded DOCX media to a local assets directory."""

from __future__ import annotations

from pathlib import Path

from documind.reader.package_reader import DocxPackage


class MediaExporter:
    def export(self, package: DocxPackage, out_dir: Path, assets_dir_name: str = "assets") -> dict[str, str]:
        assets_dir = Path(out_dir) / assets_dir_name
        assets_dir.mkdir(parents=True, exist_ok=True)

        mapping: dict[str, str] = {}
        for index, (target, content) in enumerate(sorted(package.media_files.items()), start=1):
            suffix = Path(target).suffix or ".bin"
            filename = f"img_{index:03d}{suffix.lower()}"
            output_path = assets_dir / filename
            output_path.write_bytes(content)
            mapping[target] = f"./{assets_dir_name}/{filename}"

        package.asset_map = mapping
        return mapping

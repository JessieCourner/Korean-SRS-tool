from pathlib import Path


source = Path(__file__).with_name("korean_bunpro_app.py")
exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), globals())

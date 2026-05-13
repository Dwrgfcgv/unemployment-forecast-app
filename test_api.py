from src.data_pipeline import build_official_dataset


dataset, source_catalog, metadata = build_official_dataset()

print(dataset.tail())
print()
print(source_catalog[["Показатель", "Источник", "Формат"]].head())
print()
print(metadata)

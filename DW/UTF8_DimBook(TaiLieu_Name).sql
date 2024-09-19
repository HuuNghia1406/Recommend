use library_warehouse

UPDATE DimBook
SET Tailieu_Name = LOWER(REPLACE(TRIM(SUBSTRING(Tailieu_Name, CHARINDEX('$a', Tailieu_Name) + 2, LEN(Tailieu_Name))), '/', ''))
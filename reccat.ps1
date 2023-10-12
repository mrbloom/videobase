.# Check if a parameter is provided. If not, default to the current folder.
if ($args.Count -eq 0) {
    $folderPath = Get-Location
} else {
    $folderPath = $args[0]
}

# Ensure the folder exists
if (-not (Test-Path $folderPath -PathType Container)) {
    Write-Host "The specified path does not exist or is not a directory." -ForegroundColor Red
    exit
}

# Change the current location to the provided folder
Set-Location -Path $folderPath

# 1. Show tree structure of the current folder
Write-Host "Tree structure of the current folder:" -ForegroundColor Cyan
tree

# 2. Recursively print the contents of .py, .js, .html, and .css files
$extensions = @('*.py', '*.js', '*.html', '*.css')

foreach ($ext in $extensions) {
    # Exclude the files in 'venv' directory
    $files = Get-ChildItem -Recurse -Filter $ext | Where-Object { $_.FullName -notmatch '\\venv\\' }

    foreach ($file in $files) {
        Write-Host "`n`nPrinting content of file: $file" -ForegroundColor Green
        cat $file.FullName
        Write-Host "`n`n--- End of $file ---`n`n" -ForegroundColor Red
    }
}

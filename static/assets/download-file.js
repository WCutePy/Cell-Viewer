

function fileDownloader(csvContent, fileName) {
    return function () {
        event.preventDefault();
        const internalCsvContent = csvContent();
        const blob = new Blob([internalCsvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;  // Simulates the Content-Disposition header
        a.click();
        URL.revokeObjectURL(url);
    };
}
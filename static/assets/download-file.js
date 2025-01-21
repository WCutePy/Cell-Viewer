

function fileDownloaderCsv(csvContent, fileName) {
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


function fileDownloaderXlsx(csvContent, fileName) {
    return function () {
        event.preventDefault();

        const binaryContent = csvContent();
        const byteArray = new Uint8Array(binaryContent.length);
        for (let i = 0; i < binaryContent.length; i++) {
            byteArray[i] = binaryContent.charCodeAt(i);
        }

        const blob = new Blob([byteArray], {type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;  // Simulates the Content-Disposition header
        a.click();
        URL.revokeObjectURL(url);
    };
}
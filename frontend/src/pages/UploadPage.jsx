import PDFUploader from "../components/PDFUploader";

function UploadPage() {

  return (
    <div className="upload-page">

      <div className="upload-container">

        <h1 className="upload-title">
          AI Contract Analyzer
        </h1>

        <p className="upload-subtitle">
          Upload your contract to extract key financial insights instantly
        </p>

        <PDFUploader />

      </div>

    </div>
  );

}

export default UploadPage;
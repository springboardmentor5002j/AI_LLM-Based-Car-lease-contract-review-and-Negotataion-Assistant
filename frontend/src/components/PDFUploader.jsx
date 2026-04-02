import { useDropzone } from "react-dropzone";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function PDFUploader() {

  const navigate = useNavigate();

  const onDrop = async (acceptedFiles) => {

    const file = acceptedFiles[0];

    const formData = new FormData();
    formData.append("file", file);

    const response = await axios.post(
      "http://127.0.0.1:8000/upload-pdf",
      formData
    );

    localStorage.setItem(
      "contractData",
      JSON.stringify(response.data)
    );

    navigate("/dashboard");

  };

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: { "application/pdf": [] }
  });

  return (
    <div className="upload-box" {...getRootProps()}>

      <input {...getInputProps()} />

      <p className="upload-text">
        Drag & drop your PDF contract here
      </p>

    </div>
  );

}

export default PDFUploader;
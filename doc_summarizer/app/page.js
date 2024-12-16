"use client";
import { useState } from "react";
import axios from "axios";
import { useRouter } from "next/navigation";

export default function Home() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const router = useRouter();

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!file) {
      setMessage("Please select a file to upload.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://127.0.0.1:8000/upload/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setMessage(response.data.message + " " + response.data.filename);
    } catch (error) {
      setMessage(
        error.response?.data?.detail || "An error occurred while uploading the file."
      );
    }
  };

  const navigateToSummaryPage = () => {
    router.push("/summary");
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white shadow-md rounded px-8 pt-6 pb-8 w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-4">File Upload</h1>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="file">
              Select File
            </label>
            <input
              type="file"
              id="file"
              className="w-full px-3 py-2 border rounded shadow focus:outline-none focus:shadow-outline"
              onChange={handleFileChange}
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-500 text-white font-bold py-2 px-4 rounded hover:bg-blue-700 focus:outline-none focus:shadow-outline mb-4"
          >
            Upload
          </button>
        </form>
        <button
          onClick={navigateToSummaryPage}
          className="w-full bg-green-500 text-white font-bold py-2 px-4 rounded hover:bg-green-700 focus:outline-none focus:shadow-outline"
        >
          View Summaries
        </button>
        {message && (
          <div className="mt-4 p-2 bg-gray-200 text-center rounded text-sm text-gray-700">
            {message}
          </div>
        )}
      </div>
    </div>
  );
}

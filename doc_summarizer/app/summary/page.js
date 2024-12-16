"use client";
import { useEffect, useState } from "react";
import axios from "axios";

export default function Summary() {
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchSummaries = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:8000/summaries/");
        setSummaries(response.data);
        setLoading(false);
      } catch (err) {
        setError("Failed to fetch summaries. Please try again later.");
        setLoading(false);
      }
    };

    fetchSummaries();
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white shadow-md rounded px-8 pt-6 pb-8 w-full max-w-3xl">
        <h1 className="text-2xl font-bold text-center mb-4">File Summaries</h1>
        {loading ? (
          <p className="text-center text-gray-600">Loading...</p>
        ) : error ? (
          <p className="text-center text-red-600">{error}</p>
        ) : (
          <table className="min-w-full bg-white border border-gray-200 rounded shadow">
            <thead>
              <tr>
                <th className="py-2 px-4 bg-gray-200 text-left text-sm font-bold text-gray-700 border-b">
                  Filename
                </th>
                <th className="py-2 px-4 bg-gray-200 text-left text-sm font-bold text-gray-700 border-b">
                  Summary
                </th>
              </tr>
            </thead>
            <tbody>
              {summaries.map((summary, index) => (
                <tr key={index} className="hover:bg-gray-100">
                  <td className="py-2 px-4 border-b">
                    <a
                      href={`http://127.0.0.1:8000/download/${summary.filename}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-500 hover:underline"
                    >
                      {summary.filename}
                    </a>
                  </td>
                  <td className="py-2 px-4 border-b">{summary.summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

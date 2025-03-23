import React, { useState } from 'react';
import { Upload, Loader2 } from 'lucide-react';



const FileUpload = ({ onUpload, isLoading }) => {
  const [attendanceFile, setAttendanceFile] = useState<File | null>(null);
  const [payrollFile, setPayrollFile] = useState<File | null>(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (attendanceFile && payrollFile) {
      onUpload(attendanceFile, payrollFile);
    }
  };

  return (
    <div className="bg-white shadow sm:rounded-lg mb-6">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          Upload Files for Comparison
        </h3>
        <form onSubmit={handleSubmit} className="mt-5">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Attendance File
              </label>
              <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                <div className="space-y-1 text-center">
                  <Upload className="mx-auto h-12 w-12 text-gray-400" />
                  <div className="flex text-sm text-gray-600">
                    <label className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500">
                      <span>Upload attendance file</span>
                      <input
                        type="file"
                        className="sr-only"
                        accept=".xlsx,.xls,.csv"
                        onChange={(e) => setAttendanceFile(e.target.files?.[0] || null)}
                      />
                    </label>
                  </div>
                  <p className="text-xs text-gray-500">Excel or CSV files only</p>
                </div>
              </div>
              {attendanceFile && (
                <p className="mt-2 text-sm text-gray-500">
                  Selected: {attendanceFile.name}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Payroll File
              </label>
              <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                <div className="space-y-1 text-center">
                  <Upload className="mx-auto h-12 w-12 text-gray-400" />
                  <div className="flex text-sm text-gray-600">
                    <label className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500">
                      <span>Upload payroll file</span>
                      <input
                        type="file"
                        className="sr-only"
                        accept=".xlsx,.xls,.csv"
                        onChange={(e) => setPayrollFile(e.target.files?.[0] || null)}
                      />
                    </label>
                  </div>
                  <p className="text-xs text-gray-500">Excel or CSV files only</p>
                </div>
              </div>
              {payrollFile && (
                <p className="mt-2 text-sm text-gray-500">
                  Selected: {payrollFile.name}
                </p>
              )}
            </div>
          </div>

          <div className="mt-5">
            <button
              type="submit"
              disabled={!attendanceFile || !payrollFile || isLoading}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" />
                  Processing...
                </>
              ) : (
                'Compare Files'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FileUpload;
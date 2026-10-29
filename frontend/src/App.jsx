import React, { useEffect, useState } from "react";

const API_BASE_URL = "http://localhost:5000";

function App() {
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({
    total_alerts: 0,
    restricted: 0,
    suspicious: 0,
    theft: 0,
    fight: 0
  });

  const [selectedFilter, setSelectedFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  const filteredAlerts =
    selectedFilter === "all"
      ? alerts
      : alerts.filter((alert) => alert.type === selectedFilter);

  const fetchData = () => {
    fetch(`${API_BASE_URL}/api/alerts`)
      .then((res) => res.json())
      .then((data) => {
        setAlerts(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Failed to fetch alerts:", error);
        setLoading(false);
      });

    fetch(`${API_BASE_URL}/api/stats`)
      .then((res) => res.json())
      .then((data) => setStats(data))
      .catch((error) => console.error("Failed to fetch stats:", error));
  };

  useEffect(() => {
    fetchData();

    const interval = setInterval(fetchData, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <h1 className="text-3xl font-bold mb-2">AI CCTV Dashboard</h1>

      <p className="text-slate-400 mb-6">
        Frontend connected to Flask backend
      </p>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-8">
        <h2 className="text-xl font-bold mb-4">Live CCTV Feed</h2>

        <img
          src={`${API_BASE_URL}/api/live`}
          alt="Live CCTV Feed"
          className="w-full max-h-[500px] object-contain rounded-lg bg-black"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <p className="text-slate-400">Total Alerts</p>
          <h2 className="text-3xl font-bold">{stats.total_alerts}</h2>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <p className="text-slate-400">Restricted</p>
          <h2 className="text-3xl font-bold text-red-400">
            {stats.restricted}
          </h2>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <p className="text-slate-400">Suspicious</p>
          <h2 className="text-3xl font-bold text-yellow-400">
            {stats.suspicious}
          </h2>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <p className="text-slate-400">Theft</p>
          <h2 className="text-3xl font-bold text-orange-400">
            {stats.theft}
          </h2>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <p className="text-slate-400">Fight</p>
          <h2 className="text-3xl font-bold text-purple-400">
            {stats.fight}
          </h2>
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Recent Alerts</h2>

        <button
          onClick={fetchData}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
        >
          Refresh
        </button>
      </div>

      <div className="flex flex-wrap gap-3 mb-6">
        {["all", "restricted", "suspicious", "theft", "fight"].map((filter) => (
          <button
            key={filter}
            onClick={() => setSelectedFilter(filter)}
            className={`px-4 py-2 rounded-lg font-semibold ${
              selectedFilter === filter
                ? "bg-blue-600 text-white"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            {filter.toUpperCase()}
          </button>
        ))}
      </div>

      {loading && <p className="text-slate-400">Loading alerts...</p>}

      {!loading && filteredAlerts.length === 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <p className="text-slate-400">No alerts found for this filter.</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAlerts.map((alert) => (
          <div
            key={`${alert.type}-${alert.filename}`}
            className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden"
          >
            <img
              src={alert.image_url}
              alt={alert.type}
              className="w-full h-56 object-cover"
            />

            <div className="p-4">
              <h3 className="text-lg font-bold uppercase">{alert.type}</h3>

              <p className="text-slate-400 text-sm mt-1">
                {alert.date_time}
              </p>

              <p className="text-slate-500 text-xs mt-2 break-all">
                {alert.filename}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-10 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800">
          <h2 className="text-xl font-bold">Alert History</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-800 text-slate-300">
              <tr>
                <th className="p-3">Type</th>
                <th className="p-3">Date & Time</th>
                <th className="p-3">Filename</th>
                <th className="p-3">Image</th>
              </tr>
            </thead>

            <tbody>
              {filteredAlerts.map((alert) => (
                <tr
                  key={`table-${alert.type}-${alert.filename}`}
                  className="border-b border-slate-800"
                >
                  <td className="p-3 uppercase font-semibold">
                    {alert.type}
                  </td>

                  <td className="p-3 text-slate-300">
                    {alert.date_time}
                  </td>

                  <td className="p-3 text-slate-400 break-all">
                    {alert.filename}
                  </td>

                  <td className="p-3">
                    <a
                      href={alert.image_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-400 hover:underline"
                    >
                      View
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default App;
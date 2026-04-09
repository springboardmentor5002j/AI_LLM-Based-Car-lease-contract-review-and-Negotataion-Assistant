import LoanChart from "../components/LoanChart";
import { Link } from "react-router-dom";
import { NavLink } from "react-router-dom";


function Dashboard() {

    const contractData = JSON.parse(
        localStorage.getItem("contractData")
    );

    return (
        <div className="dashboard">

            <div className="sidebar">

                <h2>Contract AI</h2>

                <ul>

                    <li>
                        <NavLink to="/dashboard">Dashboard</NavLink>
                    </li>

                    <li>
                        <NavLink to="/">Upload Contract</NavLink>
                    </li>

                    <li>
                        <NavLink to="/reports">Reports</NavLink>
                    </li>

                </ul>

            </div>

            <div className="main">

                <h1>Contract Analysis</h1>

                <div className="metrics">

                    <div className="card">
                        <h3>APR</h3>
                        <p>{contractData.contract_details.apr_percent}%</p>
                    </div>

                    <div className="card">
                        <h3>Loan Term</h3>
                        <p>{contractData.contract_details.term_months} months</p>
                    </div>

                    <div className="card">
                        <h3>Monthly Payment</h3>
                        <p>{contractData.contract_details.monthly_payment || "N/A"}</p>
                    </div>

                    <div className="card">
                        <h3>Down Payment</h3>
                        <p>{contractData.contract_details.down_payment || "N/A"}</p>
                    </div>

                </div>

                <div className="card">

                    <h2>AI Contract Summary</h2>

                    <p>{contractData.summary}</p>

                </div>

                <div className="card">

                    <h2>Negotiation Suggestions</h2>

                    <ul>
                        {contractData.negotiation_suggestions.map((s, i) => (
                            <li key={i}>{s}</li>
                        ))}
                    </ul>

                </div>

                <div className="card">

                    <h2>Loan Visualization</h2>

                    <LoanChart
                        apr={parseFloat(contractData.contract_details.apr_percent)}
                        term={parseInt(contractData.contract_details.term_months)}
                    />

                </div>

            </div>

        </div>
    );

}

export default Dashboard;
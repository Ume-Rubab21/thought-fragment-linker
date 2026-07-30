import { useEffect, useMemo, useState } from 'react'
import AppShell from '../components/AppShell'
import Icon from '../components/Icon'
import { getModelCallDashboard } from '../api'
import './ModelRoutingDashboard.css'


function formatUsd(value) {
  const numericValue = Number(value || 0)

  if (numericValue === 0) {
    return '$0.000000'
  }

  return numericValue.toLocaleString(
    undefined,
    {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 6,
      maximumFractionDigits: 8,
    },
  )
}


function formatDecision(value) {
  return String(value || '')
    .split('-')
    .map(
      (part) =>
        part.charAt(0).toUpperCase() +
        part.slice(1),
    )
    .join(' ')
}


function MetricCard({
  label,
  value,
  helper,
  icon,
}) {
  return (
    <article className="routing-metric">
      <span className="routing-metric__icon">
        <Icon name={icon} size={19} />
      </span>

      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{helper}</small>
      </div>
    </article>
  )
}


export default function ModelRoutingDashboard() {
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getModelCallDashboard(50)
      .then(setDashboard)
      .catch((requestError) => {
        setError(requestError.message)
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  const summary = dashboard?.summary

  const maximumDecisionCount = useMemo(
    () =>
      Math.max(
        1,
        ...(
          summary?.routing_decisions || []
        ).map((item) => item.count),
      ),
    [summary],
  )

  return (
    <AppShell
      title="Model routing"
      subtitle="Usage, routing decisions, latency and estimated AI cost"
      contentClassName="routing-dashboard-page"
    >
      {error && (
        <div className="alert alert--error">
          {error}
        </div>
      )}

      {loading ? (
        <div className="routing-loading">
          Loading model-call analytics…
        </div>
      ) : (
        <>
          <section className="routing-metrics-grid">
            <MetricCard
              label="Total calls"
              value={summary?.total_calls || 0}
              helper={`${summary?.successful_calls || 0} successful`}
              icon="brain"
            />

            <MetricCard
              label="Small model"
              value={summary?.small_model_calls || 0}
              helper="Lower-cost routed calls"
              icon="link"
            />

            <MetricCard
              label="Large model"
              value={summary?.large_model_calls || 0}
              helper="Ambiguous cases escalated"
              icon="dashboard"
            />

            <MetricCard
              label="Estimated savings"
              value={formatUsd(
                summary?.estimated_savings_usd,
              )}
              helper={`${summary?.savings_percentage || 0}% versus all-large routing`}
              icon="check"
            />
          </section>

          <section className="routing-dashboard-grid">
            <article className="panel routing-breakdown">
              <div className="panel__header">
                <div>
                  <span className="section-eyebrow">
                    Decision breakdown
                  </span>
                  <h2>Why each model was selected</h2>
                </div>
              </div>

              {summary?.routing_decisions?.length ? (
                <div className="routing-bars">
                  {summary.routing_decisions.map(
                    (item) => (
                      <div
                        className="routing-bar"
                        key={item.routing_decision}
                      >
                        <div className="routing-bar__copy">
                          <span>
                            {formatDecision(
                              item.routing_decision,
                            )}
                          </span>
                          <strong>{item.count}</strong>
                        </div>

                        <div className="routing-bar__track">
                          <i
                            style={{
                              width: `${
                                (
                                  item.count /
                                  maximumDecisionCount
                                ) * 100
                              }%`,
                            }}
                          />
                        </div>
                      </div>
                    ),
                  )}
                </div>
              ) : (
                <div className="empty-state compact-empty">
                  Process a Brain Dump to create the first
                  routing record.
                </div>
              )}
            </article>

            <article className="panel routing-cost-card">
              <div className="panel__header">
                <div>
                  <span className="section-eyebrow">
                    Cost overview
                  </span>
                  <h2>Routed versus all-large</h2>
                </div>
              </div>

              <dl>
                <div>
                  <dt>Actual routed cost</dt>
                  <dd>
                    {formatUsd(
                      summary?.actual_cost_usd,
                    )}
                  </dd>
                </div>

                <div>
                  <dt>Estimated all-large cost</dt>
                  <dd>
                    {formatUsd(
                      summary?.estimated_all_large_cost_usd,
                    )}
                  </dd>
                </div>

                <div className="is-saving">
                  <dt>Estimated savings</dt>
                  <dd>
                    {formatUsd(
                      summary?.estimated_savings_usd,
                    )}
                  </dd>
                </div>

                <div>
                  <dt>Average latency</dt>
                  <dd>
                    {Math.round(
                      summary?.average_latency_ms || 0,
                    )}{' '}
                    ms
                  </dd>
                </div>

                <div>
                  <dt>Total tokens</dt>
                  <dd>
                    {(
                      summary?.total_tokens || 0
                    ).toLocaleString()}
                  </dd>
                </div>
              </dl>

              <p className="routing-cost-note">
                Savings remain zero until real model prices
                are configured in the backend environment.
              </p>
            </article>
          </section>

          <section className="panel routing-history">
            <div className="panel__header">
              <div>
                <span className="section-eyebrow">
                  Recent history
                </span>
                <h2>Latest model calls</h2>
              </div>

              <span className="routing-history__count">
                {dashboard?.calls?.length || 0} shown
              </span>
            </div>

            {dashboard?.calls?.length ? (
              <div className="routing-table-wrap">
                <table className="routing-table">
                  <thead>
                    <tr>
                      <th>Route</th>
                      <th>Model</th>
                      <th>Similarity</th>
                      <th>Tokens</th>
                      <th>Latency</th>
                      <th>Cost</th>
                      <th>Status</th>
                    </tr>
                  </thead>

                  <tbody>
                    {dashboard.calls.map((call) => (
                      <tr key={call.id}>
                        <td>
                          <span
                            className={`route-pill route-pill--${call.model_tier}`}
                          >
                            {formatDecision(
                              call.routing_decision,
                            )}
                          </span>
                        </td>

                        <td>
                          <strong>{call.model_name}</strong>
                          <small>{call.provider}</small>
                        </td>

                        <td>
                          {call.highest_similarity === null
                            ? '—'
                            : Number(
                                call.highest_similarity,
                              ).toFixed(3)}
                        </td>

                        <td>
                          {call.total_tokens.toLocaleString()}
                        </td>

                        <td>{call.latency_ms} ms</td>

                        <td>
                          {formatUsd(
                            call.estimated_cost_usd,
                          )}
                        </td>

                        <td>
                          <span
                            className={
                              call.success
                                ? 'call-status is-success'
                                : 'call-status is-failed'
                            }
                          >
                            {call.success
                              ? 'Success'
                              : 'Failed'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state compact-empty">
                No model calls have been recorded yet.
              </div>
            )}
          </section>
        </>
      )}
    </AppShell>
  )
}

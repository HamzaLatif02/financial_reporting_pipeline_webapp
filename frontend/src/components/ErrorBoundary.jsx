import { Component } from 'react'
import { AlertTriangle } from 'lucide-react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, message: '' }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message ?? 'Unknown error' }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center px-6">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm px-10 py-10
                          flex flex-col items-center gap-5 text-center max-w-sm w-full">
            <AlertTriangle size={40} className="text-amber-500" />
            <div>
              <p className="font-semibold text-slate-800 text-lg">Something went wrong</p>
              <p className="text-sm text-slate-500 mt-1">{this.state.message}</p>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="px-5 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium
                         hover:bg-blue-700 transition-colors"
            >
              Reload
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

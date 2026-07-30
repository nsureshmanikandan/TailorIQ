import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="card border-red-200 bg-red-50 text-center py-8">
          <h2 className="text-lg font-medium text-red-700">Something went wrong</h2>
          <p className="text-sm text-red-600 mt-2">Please refresh the page and try again.</p>
        </div>
      )
    }
    return this.props.children
  }
}

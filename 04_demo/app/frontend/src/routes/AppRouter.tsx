import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { DashboardPage } from '../features/cases/DashboardPage'
import { CaseWorkspacePage } from '../features/cases/CaseWorkspacePage'
import { ReviewBoardPage } from '../features/cases/ReviewBoardPage'

export function AppRouter() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="cases/:caseId" element={<CaseWorkspacePage />} />
        <Route path="review" element={<ReviewBoardPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

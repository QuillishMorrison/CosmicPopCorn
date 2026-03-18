import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthPage } from '../features/auth/AuthPage'

test('renders auth landing content', () => {
  render(
    <BrowserRouter>
      <AuthPage />
    </BrowserRouter>
  )
  expect(
    screen.getByText(
      /\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u0430\u0432\u0442\u043e\u043d\u043e\u043c\u043d\u043e\u0439 \u0441\u0442\u0430\u043d\u0446\u0438\u0435\u0439/i
    )
  ).toBeInTheDocument()
})

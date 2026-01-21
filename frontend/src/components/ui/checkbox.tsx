"use client"

import * as React from "react"

export interface CheckboxProps {
  checked: boolean
  onCheckedChange: (checked: boolean) => void
  id?: string
  className?: string
  disabled?: boolean
}

export function Checkbox({ 
  checked, 
  onCheckedChange, 
  id, 
  className = "",
  disabled = false,
  ...props 
}: CheckboxProps) {
  return (
    <input
      type="checkbox"
      id={id}
      checked={checked}
      disabled={disabled}
      onChange={(e) => onCheckedChange(e.target.checked)}
      className={`h-4 w-4 rounded border border-input bg-background ${className}`}
      {...props}
    />
  )
}